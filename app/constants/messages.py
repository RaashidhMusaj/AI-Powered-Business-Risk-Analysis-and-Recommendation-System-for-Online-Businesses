class APIMessages:
    """
    Standardized API User Messages.
    """
    SUCCESS_HEALTH_CHECK = "Health check completed successfully."
    SUCCESS_VERSION_CHECK = "Version information retrieved successfully."
    SUCCESS_ANALYSIS = "Product business risk analysis completed successfully."
    
    ERROR_INVALID_URL = "The provided product URL is invalid or unsupported."
    ERROR_SCRAPING_FAILED = "Failed to scrape product data from the provided URL."
    ERROR_AI_INFERENCE = "AI inference pipeline encountered an internal error."
    ERROR_AGGREGATION_FAILED = "Statistical risk aggregation failed."
    ERROR_INTERNAL_SERVER = "An unexpected internal server error occurred."
    
    PHASE_2_NOT_IMPLEMENTED = "This endpoint is scheduled for integration in Phase 2."
