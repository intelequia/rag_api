import exiftool

def getFileMetadata(path: str,data):
  data[-1].page_content = data[-1].page_content + "\n" +"Metadatos: \n"

  try:
    with exiftool.ExifToolHelper() as et:
      metadata = et.get_metadata(path)
      for key in metadata[0].keys():
        data[-1].page_content += (f"{key}: {metadata[0][key]} \n")
          
      return data
      
  except Exception as e:
    return {"message": "An error occurred while adding documents.", "error": str(e)}