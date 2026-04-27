from datetime import datetime

import narwhals as nw
from narwhals.typing import IntoFrame


def _compute_imputation_datetime(df: nw.DataFrame) -> datetime:
    """Return the earliest non-null creation time found across all three process
    creation time columns.  Falls back to datetime(1970, 1, 1) if every value
    is null.
    """
    if isinstance(df, nw.LazyFrame):
        df = df.collect()
    candidates: list[datetime] = []
    for col in (
        "TargetProcessCreationTime",
        "ActingProcessCreationTime",
        "ParentProcessCreationTime",
    ):
        if col not in df.columns:
            continue
        val = df.select(nw.col(col).min()).item(0, 0)
        if val is not None:
            candidates.append(val)
    return min(candidates) if candidates else datetime(1970, 1, 1)


def _coalesce_acting_parent(df: nw.DataFrame) -> nw.DataFrame:
    """Normalize Acting/Parent/Target process triplets to sentinel values.

    Fills SQL nulls and the literal string "null" with sentinels:
      PID  → -1   (null or 0; PID 0 is System Idle, not a real parent)
      name → "MISSING"
      time → epoch
    """
    epoch = datetime(1970, 1, 1)

    def _pid(col: str) -> nw.Expr:
        return nw.when(
            nw.col(col).is_null() | (nw.col(col) == nw.lit(0))
        ).then(nw.lit(-1)).otherwise(nw.col(col))

    def _name(col: str) -> nw.Expr:
        return nw.when(
            nw.col(col).is_null() | (nw.col(col) == nw.lit("null"))
        ).then(nw.lit("MISSING")).otherwise(nw.col(col))

    def _time(col: str) -> nw.Expr:
        # Cast epoch literal to us to match column precision — nw.lit(datetime) defaults to
        # Datetime(s) on the ibis backend which downgrades the column on coalesce.
        return nw.coalesce(nw.col(col), nw.lit(epoch).cast(nw.Datetime("us")))

    return df.with_columns(
        TargetProcessId=_pid("TargetProcessId"),
        TargetProcessFilename=_name("TargetProcessFilename"),
        ActingProcessId=_pid("ActingProcessId"),
        ActingProcessFilename=_name("ActingProcessFilename"),
        ActingProcessCreationTime=_time("ActingProcessCreationTime"),
        ParentProcessId=_pid("ParentProcessId"),
        ParentProcessFilename=_name("ParentProcessFilename"),
        ParentProcessCreationTime=_time("ParentProcessCreationTime"),
    )


def _resolve_epoch_times(df: nw.DataFrame) -> nw.DataFrame:
    """Substitute epoch acting/parent timestamps with the real creation time.

    When MDE records a null InitiatingProcessCreationTime, it collapses to epoch
    after coalescing. If that PID appears as a TargetProcessId elsewhere in the
    same dataset with exactly one distinct non-epoch creation time, we can patch
    the reference. This prevents duplicate synthetic nodes (PID|epoch) and
    (PID|real_time) for the same physical process.

    PIDs with multiple distinct creation times (PID recycled across reboots) are
    left untouched — they're genuinely ambiguous.
    """
    # Collect to eager: this function does multi-table self-joins and concat
    # which require a materialised frame with a consistent schema.
    if isinstance(df, nw.LazyFrame):
        df = df.collect()
    epoch = datetime(1970, 1, 1)

    # Step 1: pool all non-epoch, non-zero PID observations from every role into
    # a single (Pid, Filename, Time) table — this is the evidence base of known
    # creation times across the whole dataset.
    target_times = (
        df.filter(
            (nw.col("TargetProcessCreationTime") != nw.lit(epoch))
            & (nw.col("TargetProcessId") > nw.lit(0))
        )
        .select(
            nw.col("TargetProcessId").alias("Pid"),
            nw.col("TargetProcessFilename").alias("Filename"),
            nw.col("TargetProcessCreationTime").alias("Time"),
        )
    )
    acting_times = (
        df.filter(
            (nw.col("ActingProcessCreationTime") != nw.lit(epoch))
            & (nw.col("ActingProcessId") > nw.lit(0))
        )
        .select(
            nw.col("ActingProcessId").alias("Pid"),
            nw.col("ActingProcessFilename").alias("Filename"),
            nw.col("ActingProcessCreationTime").alias("Time"),
        )
    )
    parent_times = (
        df.filter(
            (nw.col("ParentProcessCreationTime") != nw.lit(epoch))
            & (nw.col("ParentProcessId") > nw.lit(0))
        )
        .select(
            nw.col("ParentProcessId").alias("Pid"),
            nw.col("ParentProcessFilename").alias("Filename"),
            nw.col("ParentProcessCreationTime").alias("Time"),
        )
    )
    # Step 2: collapse to unambiguous (PID, filename) → time.
    # n_unique == 1 means all roles agree on exactly one creation time — safe to use.
    # n_unique > 1 means PID recycled with same filename — genuinely ambiguous, skip and warn.
    all_times = (
        nw.concat([target_times, acting_times, parent_times])
        .group_by("Pid", "Filename")
        .agg(
            nw.col("Time").n_unique().alias("n_times"),
            nw.col("Time").min().alias("ResolvedCreationTime"),
        )
    )
    ambiguous = all_times.filter(nw.col("n_times") > nw.lit(1))
    if len(ambiguous) > 0:
        import warnings
        rows = ambiguous.select("Pid", "Filename", "n_times").to_arrow().to_pylist()
        warnings.warn(
            f"_resolve_epoch_times: {len(rows)} (PID, filename) pair(s) observed with multiple "
            f"distinct creation times — likely PID recycling, epoch references for these will not be patched: "
            + ", ".join(f"{r['Filename']}(PID {r['Pid']}, {r['n_times']} times)" for r in rows[:5])
            + ("..." if len(rows) > 5 else ""),
            stacklevel=3,
        )
    pid_lookup = all_times.filter(nw.col("n_times") == nw.lit(1)).drop("n_times")

    # Step 3: secondary PID-only lookup for rows where acting/parent filename is MISSING
    # (the (PID, filename) join from step 2 would never match "MISSING").
    # Only include PIDs that resolve to exactly one time across all filenames —
    # otherwise the PID is recycled and we can't safely pick a winner.
    pid_only_lookup = (
        pid_lookup
        .group_by("Pid")
        .agg(
            nw.col("ResolvedCreationTime").n_unique().alias("n"),
            nw.col("ResolvedCreationTime").min().alias("ResolvedCreationTime"),
        )
        .filter(nw.col("n") == nw.lit(1))
        .drop("n")
    )

    def _resolve(df: nw.DataFrame, pid_col: str, filename_col: str, time_col: str) -> nw.DataFrame:
        # Step 4: patch epoch references with the real creation time.
        # Pass 1: join on (PID, filename) — covers the normal case.
        df = (
            df.join(
                pid_lookup.rename({"Pid": pid_col, "Filename": filename_col, "ResolvedCreationTime": "_resolved"}),
                on=[pid_col, filename_col],
                how="left",
            )
            .with_columns(
                **{time_col: nw.when(
                    (nw.col(time_col) == nw.lit(epoch)) & (~nw.col("_resolved").is_null())
                ).then(nw.col("_resolved")).otherwise(nw.col(time_col))}
            )
            .drop("_resolved")
        )
        # Pass 2: PID-only fallback for rows still at epoch with MISSING filename.
        df = (
            df.join(
                pid_only_lookup.rename({"Pid": pid_col, "ResolvedCreationTime": "_resolved2"}),
                on=pid_col,
                how="left",
            )
            .with_columns(
                **{time_col: nw.when(
                    (nw.col(time_col) == nw.lit(epoch))
                    & (nw.col(filename_col) == nw.lit("MISSING"))
                    & (~nw.col("_resolved2").is_null())
                ).then(nw.col("_resolved2")).otherwise(nw.col(time_col))}
            )
            .drop("_resolved2")
        )
        return df

    result = _resolve(df, "ActingProcessId", "ActingProcessFilename", "ActingProcessCreationTime")
    result = _resolve(result, "ParentProcessId", "ParentProcessFilename", "ParentProcessCreationTime")
    return result


def _impute_creation_times(df: nw.DataFrame, min_dt: datetime) -> nw.DataFrame:
    """Fill null TargetProcessCreationTime with min_dt and flag affected rows."""
    return df.with_columns(
        ImputedCreationTime=nw.col("TargetProcessCreationTime").is_null(),
        TargetProcessCreationTime=nw.coalesce(
            nw.col("TargetProcessCreationTime"), nw.lit(min_dt)
        ),
    )


def prepare_events(
    events: IntoFrame, source: str, impute_date_times: bool = True
) -> nw.DataFrame:
    """Prepare events from different telemetry sources into a unified schema.

    Parameters
    ----------
    events : any narwhals-compatible dataframe (pandas, polars, ibis, …)
        The raw events table.
    source : str
        One of "mde" or "volatility".
    impute_date_times : bool
        When True (default), null creation times are filled with the earliest
        non-null timestamp found in the dataset and an ``ImputedCreationTime``
        boolean column is added to mark affected rows.

    Returns
    -------
    narwhals.DataFrame
        A frame with unified column names (Target/Acting/Parent process triplets).
    """
    source_key = source.lower()
    if source_key == "mde":
        return prepare_mde_data(events, impute_date_times=impute_date_times)
    if source_key == "volatility":
        return prepare_volatility_data(events, impute_date_times=impute_date_times)
    raise ValueError(f"Unknown source '{source}'. Expected 'mde' or 'volatility'.")


def prepare_mde_data(events: IntoFrame, impute_date_times: bool = True) -> nw.DataFrame:
    """
    Process MDE data events to map processes correctly.

    Parameters
    ----------
    impute_date_times : bool
        When True (default), null creation times are filled with the earliest
        non-null timestamp in the dataset.  Affected rows are flagged with
        ``ImputedCreationTime=True``.
    """
    df = nw.from_native(events)
    cols = df.columns
    optional_cols = []
    if "ProcessCommandLine" in cols:
        optional_cols.append(nw.col("ProcessCommandLine").alias("CommandLine"))
    else:
        optional_cols.append(nw.lit("").alias("CommandLine"))
    if "FolderPath" in cols:
        optional_cols.append(nw.col("FolderPath"))
    else:
        optional_cols.append(nw.lit("").alias("FolderPath"))

    result = (
        df.filter(nw.col("ActionType") == "ProcessCreated")
        .unique(subset=["ReportId", "Timestamp", "DeviceName"], keep="any")
        .sort("Timestamp")
        .with_columns(
            TargetProcessId=nw.col("ProcessId"),
            TargetProcessFilename=nw.col("FileName"),
            TargetProcessCreationTime=nw.col("ProcessCreationTime"),
            ActingProcessId=nw.col("InitiatingProcessId"),
            ActingProcessFilename=nw.col("InitiatingProcessFileName"),
            ActingProcessCreationTime=nw.col("InitiatingProcessCreationTime"),
            ParentProcessId=nw.col("InitiatingProcessParentId"),
            ParentProcessFilename=nw.col("InitiatingProcessParentFileName"),
            ParentProcessCreationTime=nw.col("InitiatingProcessParentCreationTime"),
            *optional_cols,
        )
    )
    result = _coalesce_acting_parent(result)
    result = _resolve_epoch_times(result)

    if impute_date_times:
        result = _impute_creation_times(result, _compute_imputation_datetime(result))

    return result


def prepare_volatility_data(
    events: IntoFrame, impute_date_times: bool = True
) -> nw.DataFrame:
    """
    Process Volatility data events from the `pstree` plugin. Adds immediate parent
    and grandparent information.

    Parameters
    ----------
    impute_date_times : bool
        When True (default), null creation times are filled with the earliest
        non-null timestamp in the dataset.  Affected rows are flagged with
        ``ImputedCreationTime=True``.
    """
    df = nw.from_native(events)

    parent = df.with_columns(
        ParentProcessId=nw.col("PID"),
        ParentProcessFilename=nw.col("ImageFileName"),
        ParentProcessCreationTime=nw.col("CreateTime"),
        ParentVolId=nw.col("_vol_id"),
    ).select(
        "ParentVolId",
        "ParentProcessId",
        "ParentProcessFilename",
        "ParentProcessCreationTime",
    )

    acting = df.with_columns(
        ActingProcessId=nw.col("PID"),
        ActingProcessFilename=nw.col("ImageFileName"),
        ActingProcessCreationTime=nw.col("CreateTime"),
        ActingVolId=nw.col("_vol_id"),
        ActingVolParentId=nw.col("_vol_parent_id"),
    ).select(
        "ActingVolId",
        "ActingVolParentId",
        "ActingProcessId",
        "ActingProcessFilename",
        "ActingProcessCreationTime",
    )

    acting_with_parent = acting.join(
        parent,
        left_on="ActingVolParentId",
        right_on="ParentVolId",
        how="left",
    )

    result = (
        df.join(
            acting_with_parent,
            left_on="_vol_parent_id",
            right_on="ActingVolId",
            how="left",
        )
        .with_columns(
            TargetProcessId=nw.col("PID"),
            TargetProcessFilename=nw.col("ImageFileName"),
            TargetProcessCreationTime=nw.col("CreateTime"),
            Timestamp=nw.col("CreateTime"),
        )
        .sort("CreateTime")
    )
    result = _coalesce_acting_parent(result)

    if impute_date_times:
        result = _impute_creation_times(result, _compute_imputation_datetime(result))

    return result


__all__ = [
    "prepare_events",
    "prepare_mde_data",
    "prepare_volatility_data",
]
