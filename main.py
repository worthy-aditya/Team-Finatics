import sys


def main():
    print("=" * 40)
    print("     SentinelAI Report Generator")
    print("=" * 40)
    print("\nSelect Report Format:")
    print("1. DOCX")
    print("2. PDF")
    print("3. Markdown")
    print("4. Exit")

    choice = input("\nEnter choice (1-4): ").strip()

    if choice == "1":
        try:
            from sentinal.research.report.generate_report import generate_docx_report
        except ModuleNotFoundError:
            print("DOCX export requires the 'python-docx' package. Install it with: pip install python-docx")
            return

        print("\nGenerating DOCX report...")
        generate_docx_report()
    elif choice == "2":
        try:
            from sentinal.research.report.generate_pdf_report import generate_pdf_report
        except ModuleNotFoundError:
            print("PDF export requires the 'fpdf' package. Install it with: pip install fpdf")
            return

        print("\nGenerating PDF report...")
        generate_pdf_report()
    elif choice == "3":
        from sentinal.research.report.generate_markdown_report import generate_markdown_report

        print("\nGenerating Markdown report...")
        generate_markdown_report()
    elif choice == "4":
        print("Exiting...")
        sys.exit(0)
    else:
        print("Invalid choice. Please run the script again and select 1, 2, 3, or 4.")


if __name__ == "__main__":
    main()