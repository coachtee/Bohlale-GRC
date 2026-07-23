from django.http import HttpResponse
from openpyxl import Workbook


def excel_response(filename, headers, rows):
    """rows: iterable of iterables (already stringified/primitive values)."""
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(headers)
    for row in rows:
        sheet.append(list(row))
    for i, header in enumerate(headers, start=1):
        sheet.column_dimensions[sheet.cell(row=1, column=i).column_letter].width = max(14, len(str(header)) + 2)

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    workbook.save(response)
    return response
