import zipfile

def get_domain(user_mail):
    # Get the domain of mail adress
    mailDomain = user_mail.split('@')[1]

    if "uni" in mailDomain:
        return "uni"
    elif "uksh" in mailDomain:
        return "uksh"
    return "unknown"

def get_user_name(user_mail):
    return user_mail.split("@")[0]

def zip_files(files, output_filename="segmentation.zip"):
    with zipfile.ZipFile(output_filename, 'w') as zipf:
        for file in files:
            zipf.write(file, arcname=file.split('/')[-1])
    return output_filename