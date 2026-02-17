
# Admin endpoint to view login history
@router.get("/admin/login-history")
def get_login_history(
    email: str = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get login history for all users or a specific user (Admin only)
    Query params:
    - email: Filter by specific user email (optional)
    - limit: Number of records to return (default 100)
    """
    query = db.query(LoginHistory)
    
    if email:
        query = query.filter(LoginHistory.email == email)
    
    login_records = query.order_by(LoginHistory.login_time.desc()).limit(limit).all()
    
    return {
        "total": len(login_records),
        "records": [
            {
                "id": record.id,
                "user_id": record.user_id,
                "email": record.email,
                "login_method": record.login_method,
                "ip_address": record.ip_address,
                "user_agent": record.user_agent,
                "success": record.success,
                "failure_reason": record.failure_reason,
                "login_time": record.login_time.isoformat() if record.login_time else None
            }
            for record in login_records
        ]
    }

@router.get("/admin/login-stats")
def get_login_stats(db: Session = Depends(get_db)):
    """
    Get login statistics (Admin only)
    """
    from sqlalchemy import func
    
    total_logins = db.query(func.count(LoginHistory.id)).scalar()
    successful_logins = db.query(func.count(LoginHistory.id)).filter(LoginHistory.success == True).scalar()
    failed_logins = db.query(func.count(LoginHistory.id)).filter(LoginHistory.success == False).scalar()
    
    # Login methods breakdown
    method_stats = db.query(
        LoginHistory.login_method,
        func.count(LoginHistory.id).label('count')
    ).group_by(LoginHistory.login_method).all()
    
    # Recent failed attempts
    recent_failures = db.query(LoginHistory).filter(
        LoginHistory.success == False
    ).order_by(LoginHistory.login_time.desc()).limit(10).all()
    
    return {
        "total_logins": total_logins,
        "successful_logins": successful_logins,
        "failed_logins": failed_logins,
        "success_rate": round((successful_logins / total_logins * 100) if total_logins > 0 else 0, 2),
        "methods": {method: count for method, count in method_stats},
        "recent_failures": [
            {
                "email": record.email,
                "method": record.login_method,
                "reason": record.failure_reason,
                "time": record.login_time.isoformat() if record.login_time else None
            }
            for record in recent_failures
        ]
    }
