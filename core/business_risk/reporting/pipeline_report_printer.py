from datetime import datetime


class PipelineReportPrinter:

    WIDTH = 80

    @staticmethod
    def line(char="─"):
        print("┌" + char * (PipelineReportPrinter.WIDTH - 2) + "┐")

    @staticmethod
    def header(title: str):
        w = PipelineReportPrinter.WIDTH
        print("╔" + "═" * (w - 2) + "╗")
        print("║" + title.upper().center(w - 2) + "║")
        print("╚" + "═" * (w - 2) + "╝")

    @staticmethod
    def section(title: str):
        w = PipelineReportPrinter.WIDTH
        print()
        print(f"─── {title.upper()} ".ljust(w, "─"))

    @staticmethod
    def meter(score: float, max_score: float = 100.0, length: int = 15) -> str:
        val = max(0.0, min(max_score, score))
        filled = int(round((val / max_score) * length))
        bar = "█" * filled + "░" * (length - filled)
        return f"[{bar}] {val:5.1f}/100"

    @staticmethod
    def print_report(
            product,
            aggregation,
            quality,
            delivery,
            trust,
            business,
    ):
        printer = PipelineReportPrinter

        printer.header("AI Business Risk Analysis - Executive Report")
        print(f"  Generated Timestamp : {datetime.now():%Y-%m-%d %H:%M:%S}")
        print(f"  System Version      : v1.0 Production Subsystem")

        # 1. Product Summary
        printer.section("Product Metadata & Target Overview")
        p_name = getattr(product, 'product_name', 'N/A')
        p_id = getattr(product, 'product_id', 'N/A')
        p_cat = getattr(product, 'category', 'N/A')
        p_url = getattr(product, 'product_url', 'N/A')
        p_revs = len(getattr(product, 'reviews', [])) if hasattr(product, 'reviews') and product.reviews else 0

        print(f"  • Product Name  : {p_name}")
        print(f"  • Product ID    : {p_id}")
        print(f"  • Category      : {p_cat}")
        print(f"  • Total Reviews : {p_revs}")
        print(f"  • Product URL   : {p_url}")

        # 2. Executive Business Risk Index
        printer.section("Executive Business Risk Evaluation")
        bri_val = getattr(business, 'business_risk_index', 0.0)
        bri_lvl = getattr(business, 'business_risk_level', 'UNKNOWN')
        print(f"  • Overall Business Risk Index : {printer.meter(bri_val)}")
        print(f"  • Overall Risk Classification : [{bri_lvl.upper()}]")

        # 3. Fuzzy Risk Breakdown
        printer.section("Fuzzy Logic Risk Aspect Breakdown")
        q_score = getattr(quality, 'score', 0.0)
        q_level = getattr(quality, 'level', 'N/A')
        d_score = getattr(delivery, 'score', 0.0)
        d_level = getattr(delivery, 'level', 'N/A')
        t_score = getattr(trust, 'score', 0.0)
        t_level = getattr(trust, 'level', 'N/A')

        print(f"  • Quality Risk  : {printer.meter(q_score)} | Rating: {q_level}")
        print(f"  • Delivery Risk : {printer.meter(d_score)} | Rating: {d_level}")
        print(f"  • Trust Risk    : {printer.meter(t_score)} | Rating: {t_level}")

        # 4. Statistical Metrics
        printer.section("Review Sentiment & AI Prediction Summary")
        if hasattr(aggregation, 'review_statistics') and aggregation.review_statistics:
            print("  [Review Metrics]")
            for k, v in aggregation.review_statistics.items():
                print(f"    - {k:<24}: {v}")

        if hasattr(aggregation, 'sentiment_statistics') and aggregation.sentiment_statistics:
            print("  [Sentiment Distribution]")
            for k, v in aggregation.sentiment_statistics.items():
                print(f"    - {k:<24}: {v}")

        print()
        print("═" * printer.WIDTH)
        print("  END OF EXECUTIVE REPORT - RISK ANALYSIS PIPELINE COMPLETE  ".center(printer.WIDTH, "═"))
        print("═" * printer.WIDTH)