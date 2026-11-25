# Suggested test cases

Use a text-based sample document with clear facts, dates, names, and definitions.

| Test | Action | Expected result |
|---|---|---|
| TC-01 | Open the home page | The Document Q&A interface loads. |
| TC-02 | Upload a TXT file with readable text | Success message and text-record count appear. |
| TC-03 | Upload a text-based PDF | PDF text is extracted and indexed. |
| TC-04 | Upload a DOCX containing paragraphs | Paragraph text is extracted and indexed. |
| TC-05 | Upload a DOCX containing a table | Table cell text is included in the knowledge base. |
| TC-06 | Ask a question using words in the document | A matching answer and source passage are displayed. |
| TC-07 | Ask for a date stated in the document | A matching date is returned when a supported date format is present. |
| TC-08 | Ask about information absent from the document | The system reports insufficient matching information. |
| TC-09 | Try an unsupported file extension | The interface displays an unsupported-file message. |
| TC-10 | Submit without choosing a file | The interface asks the user to select a document. |
| TC-11 | Try an image-only scanned PDF | The system explains that no readable text was extracted. |

Record actual results and screenshots after running each applicable test on the target computer. Do not report a test as passed until it has been performed.
