# Teodor -  Fletchers Assessment 2026 Briefing

Hi Teodor,

Here is the briefing for the round 2 interview question:

## Fletchers AI take-home assessment

This document outlines the details of the second-round take-home assessment for the role of Fullstack
Engineer at Fletchers AI. It consists of
 1. A coding assessment
 2. Some follow-up questions requiring written answers prepared for discussion, however no
    coding

### Details

A core part of our work at Fletchers AI involves being really good at extracting and processing
information from a wide variety of sometimes-arcane document formats. We must determine the correct
routing for a given document (which may not just be based on its format -- consider PDFs with
digital text vs PDFs with scanned text), extract the relevant information (eg OCR), and store it
sensibly for later retrieval. This data is then used in various agentic pipelines, where most
commonly we will feed the content (perhaps coerced into a different form) into an agent as context

Your task is to implement a limited version of this pipeline, which will work with just `.pdf`
and `.docx` files, extracting and storing their information. It should be designed with a view
towards supporting many more document formats in the future

Your solution should include
 - Methods for extracting information from the above document types
 - A design for storing extracted information in an easily retrievable way (for example via
   REST API, or agentic tool call)
 - A frontend for enabling user-upload of documents, displaying processing progress, and making
   results available in a useful way

Solutions should be submitted in Python/TypeScript (or some combination of the two)

Some more notes
 - Where you rely on external services to extract information, you may mock this (ie we do not 
   expect you to spend any money on APIs while completing this assessment)
 - You may wish to include a test suite to prove that your design works
 - You may 'zoom in' on any aspect of the above if you wish to showcase certain skills

### Further questions

For this component you need only prepare brief written answers, which will then be discussed
in more detail in the interview
 - Give a brief overview of a scalable architecture which would support this pipeline
   being run in production
 - How would your design change if you needed to support plain text files?
 - How would your design change if the number of documents being uploaded went up 100x?

### Practicalities
 - You will have 7 days to complete this assessment
 - It is expected to take around 2-3 hours to complete
 - Complete solutions should be emailed to [danwhite@fs.co.uk](mailto:danwhite@fs.co.uk),
   CCing [noahmilton@fs.co.uk](mailto:noahmilton@fs.co.uk)
 - Use of AI is permitted for this assessment, however candidates should exercise caution and judgement.
   If you are just sending us Claude's response to this document, your solution will probably not go deep
   enough, and this will be fairly obvious.


Let me know if there are any questions,

Thanks,
Dan