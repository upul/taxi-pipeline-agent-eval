tools = [
    {
        "type": "function",
        "function": {
            "name": "get_monthly_statistics",
            "description": "Get the basic monthly statistics for a given year and month.",
            "parameters": {
                "type": "object",
                "properties": {
                    "year": {
                        "type": "integer",
                        "description": "This parameter represents the year in integer format.",
                    },
                    "month": {
                        "type": "integer",
                        "description": "This parameter represents month in integer format and accepts 1 to 12 including both.",
                    },
                },
                "required": ["year", "month"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_trip_breakdown",
            "description": "Divide the trip distance into 4 buckets and for each bucket calculate number of trips and average cost",
            "parameters": {
                "type": "object",
                "properties": {
                    "year": {
                        "type": "integer",
                        "description": "This parameter represents the year in integer format.",
                    },
                    "month": {
                        "type": "integer",
                        "description": "This parameter represents month in integer format and accepts 1 to 12 including both.",
                    },
                },
                "required": ["year", "month"],
                "additionalProperties": False,
            },
        },
    },
]
