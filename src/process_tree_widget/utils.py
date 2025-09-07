import ibis

from datetime import datetime
from ibis import _


def prepare_events(events, source: str):
    """Prepare events from different telemetry sources into a unified schema.

    Parameters
    ----------
    events : ibis.Table
        The raw events table.
    source : str
        One of "mde" or "volatility".

    Returns
    -------
    ibis.Table
        A table with unified column names (Target/Acting/Parent process triplets).
    """
    source_key = source.lower()
    if source_key == "mde":
        return prepare_mde_data(events)
    if source_key == "volatility":
        return prepare_volatility_data(events)
    raise ValueError(f"Unknown source '{source}'. Expected 'mde' or 'volatility'.")


def prepare_mde_data(_events):
    """
    Process MDE data events to map processes correctly.
    """

    return (
        _events.filter(_.ActionType == "ProcessCreated")
               .distinct(on=["ReportId", "Timestamp", "DeviceName"], keep="first")
               .order_by(_.Timestamp)
               .mutate(
                    TargetProcessId=_.ProcessId,
                    TargetProcessFilename=_.FileName,
                    TargetProcessCreationTime=_.ProcessCreationTime,
                    ActingProcessId=_.InitiatingProcessId,
                    ActingProcessFilename=_.InitiatingProcessFileName,
                    ActingProcessCreationTime=_.InitiatingProcessCreationTime,
                    ParentProcessId=_.InitiatingProcessParentId,
                    ParentProcessFilename=_.InitiatingProcessParentFileName,
                    ParentProcessCreationTime=_.InitiatingProcessParentCreationTime,
                )
    )


def prepare_volatility_data(_events):
    """
    Process Volatility data events from the `pstree` plugin. Focus on adding immediate parent and grandparent information.
    """

    # Add parent (Parent_) information
    parent = (
        _events.mutate(
            ParentProcessId=_.PID,
            ParentProcessFilename=_.ImageFileName,
            ParentProcessCreationTime=_.CreateTime,
            ParentVolId=_._vol_id
        ).select(
            _.ParentVolId,
            _.ParentProcessId,
            _.ParentProcessFilename,
            _.ParentProcessCreationTime
        )
    )

    # Add acting process (Acting_) information
    acting = (
        _events.mutate(
            ActingProcessId=_.PID,
            ActingProcessFilename=_.ImageFileName,
            ActingProcessCreationTime=_.CreateTime,
            ActingVolId=_._vol_id,
            ActingVolParentId=_._vol_parent_id  # Added for correct join
        ).select(
            _.ActingVolId,
            _.ActingVolParentId,
            _.ActingProcessId,
            _.ActingProcessFilename,
            _.ActingProcessCreationTime
        )
    )

    # Join parent with acting using a left join
    acting = (
        parent.join(
            acting,
            [acting.ActingVolParentId == parent.ParentVolId],
            how="right"
        )
    )

    # Join the result with the events using a left join
    result = (
        _events.join(
            acting,
            [_events._vol_parent_id == acting.ActingVolId],
            how="left"
        )
        .mutate(
            TargetProcessId=_events.PID,
            TargetProcessFilename=_events.ImageFileName,
            TargetProcessCreationTime=_events.CreateTime,
            Timestamp=_events.CreateTime,
        )
        .mutate(
            ActingProcessId=ibis.coalesce(_.ActingProcessId, -1),
            ActingProcessFilename=ibis.coalesce(_.ActingProcessFilename, "MISSING"),
            ActingProcessCreationTime=ibis.coalesce(_.ActingProcessCreationTime, datetime(1970, 1, 1)),
            ParentProcessId=ibis.coalesce(_.ParentProcessId, -1),
            ParentProcessFilename=ibis.coalesce(_.ParentProcessFilename, "MISSING"),
            ParentProcessCreationTime=ibis.coalesce(_.ParentProcessCreationTime, datetime(1970, 1, 1)),
        )
        .order_by(_.CreateTime)
    )

    return result

__all__ = [
    "prepare_events",
    "prepare_mde_data",
    "prepare_volatility_data",
]