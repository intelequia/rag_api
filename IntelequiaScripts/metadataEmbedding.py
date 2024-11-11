import exiftool
from logging import getLogger
logger = getLogger(__name__)

def getFileMetadata(path: str,data):
  documentMetadata = data[-1]
  documentMetadata.page_content = "Metadatos: \n"

  try:
    with exiftool.ExifToolHelper() as et:
      metadata = et.get_metadata(path)
      for key in metadata[0].keys():
        documentMetadata.page_content += (f"{key}: {metadata[0][key]} \n")
          
      data.append(documentMetadata)
      return data

  except Exception as e:
    logger.error(e)
    return {"message": "An error occurred while adding documents.", "error": str(e)}
    
