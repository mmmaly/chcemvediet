PDF_CONTENT_TYPE = u'application/pdf'
ODT_CONTENT_TYPE = u'application/vnd.oasis.opendocument.text'
ODS_CONTENT_TYPE = u'application/vnd.oasis.opendocument.spreadsheet'
XLSX_CONTENT_TYPE = u'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
CSV_CONTENT_TYPE = u'text/csv'

# Spreadsheets get public copies made by ``spreadsheets.public_copies()`` instead of PDF print-outs.
SPREADSHEET_EXTENSIONS_BY_TYPE = {
    u'application/vnd.ms-excel': u'.xls',
    XLSX_CONTENT_TYPE: u'.xlsx',
    u'application/vnd.ms-excel.sheet.macroEnabled.12': u'.xlsm',
    ODS_CONTENT_TYPE: u'.ods',
    u'application/vnd.oasis.opendocument.spreadsheet-template': u'.ots',
}
SPREADSHEET_CONTENT_TYPES = tuple(SPREADSHEET_EXTENSIONS_BY_TYPE)
# Old binary files are often detected only as a generic OLE container; trust their extension.
SPREADSHEET_EXTENSIONS = (u'.xls', u'.xlsx', u'.xlsm', u'.xlsb', u'.xlt', u'.xltx', u'.ods', u'.ots')

XML_CONTENT_TYPES = (
    u'application/xml',
    u'text/xml',
)

LIBREOFFICE_CONTENT_TYPES = (
    u'application/CDFV2-corrupt',
    u'application/CDFV2-unknown',
    u'application/msword',
    u'application/vnd.ms-excel',
    u'application/vnd.ms-powerpoint',
    u'application/vnd.ms-office',
    u'application/vnd.oasis.opendocument.spreadsheet',
    u'application/vnd.oasis.opendocument.spreadsheet-template',
    u'application/vnd.oasis.opendocument.text',
    u'application/vnd.oasis.opendocument.text-template',
    u'application/vnd.oasis.opendocument.presentation',
    u'application/vnd.oasis.opendocument.presentation-template',
    u'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    u'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    u'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    u'text/html',
    u'text/plain',
    u'text/rtf',
)

IMAGEMAGICK_CONTENT_TYPES = (
    u'image/gif',
    u'image/jpeg',
    u'image/png',
    u'image/tiff',
    u'image/x-ms-bmp',
    u'image/x-portable-pixmap',
    u'image/x-portable-greymap',
    u'image/x-portable-bitmap',
    u'image/webp',
)
