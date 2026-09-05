from fastapi import FastAPI, Query

from api.services.database import get_connection


app = FastAPI(
    title="HealthBridge360 Healthcare Events API",
    version="1.0.0"
)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "healthbridge360-events-api"
    }


@app.get("/healthcare/events")
def get_events(
    page: int = Query(1, ge=1),
    page_size: int = Query(500, ge=1, le=5000)
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        offset = (page - 1) * page_size

        cursor.execute(
            """
            SELECT
                event_id,
                member_id,
                event_type,
                event_timestamp,
                event_received_timestamp,
                event_status,
                payload,
                event_source,
                api_version
            FROM healthcare_events
            ORDER BY event_timestamp, event_id
            LIMIT %s OFFSET %s
            """,
            (page_size, offset)
        )

        rows = cursor.fetchall()

        events = []

        for row in rows:
            events.append({
                "event_id": row[0],
                "member_id": row[1],
                "event_type": row[2],
                "event_timestamp": row[3].isoformat(),
                "event_received_timestamp": row[4].isoformat(),
                "event_status": row[5],
                "payload": row[6],
                "event_source": row[7],
                "api_version": row[8]
            })

        cursor.execute("SELECT COUNT(*) FROM healthcare_events")
        total_records = cursor.fetchone()[0]

        return {
            "api_version": "v1",
            "page": page,
            "page_size": page_size,
            "total_records": total_records,
            "has_more": offset + len(events) < total_records,
            "next_page": (
                page + 1
                if offset + len(events) < total_records
                else None
            ),
            "events": events
        }

    finally:
        connection.close()
