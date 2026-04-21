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
    """Fill nulls in Acting/Parent process triplets with sentinel values."""
    return df.with_columns(
        ActingProcessId=nw.coalesce(nw.col("ActingProcessId"), nw.lit(-1)),
        ActingProcessFilename=nw.coalesce(
            nw.col("ActingProcessFilename"), nw.lit("MISSING")
        ),
        ActingProcessCreationTime=nw.coalesce(
            nw.col("ActingProcessCreationTime"), nw.lit(datetime(1970, 1, 1))
        ),
        ParentProcessId=nw.coalesce(nw.col("ParentProcessId"), nw.lit(-1)),
        ParentProcessFilename=nw.coalesce(
            nw.col("ParentProcessFilename"), nw.lit("MISSING")
        ),
        ParentProcessCreationTime=nw.coalesce(
            nw.col("ParentProcessCreationTime"), nw.lit(datetime(1970, 1, 1))
        ),
    )


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
