from ibis import _

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

    # Join parent with acting
    acting = (
        parent.join(
            acting,
            [acting.ActingVolParentId == parent.ParentVolId]  # Corrected join condition
        )
    )


    # Join the result with the events
    result = (
        _events.join(
            acting,
            [_events._vol_parent_id == acting.ActingVolId]  # Corrected join condition
        ).mutate(
            TargetProcessId=_events.PID,
            TargetProcessFilename=_events.ImageFileName,
            TargetProcessCreationTime=_events.CreateTime,
        )
    )

    return result
