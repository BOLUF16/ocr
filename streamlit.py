import streamlit as st
import cv2
import re
import numpy as np
import pytesseract
import json
import easyocr



def process_image(upload_file):
    file_bytes = np.asarray(bytearray(upload_file.read()), dtype=np.uint8)
    image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    return gray

def process_nin(image):

    nin_data = {}
    
    reader = easyocr.Reader(['en'])
    result = reader.readtext(image, decoder="beamsearch", text_threshold=0.1)
    extracted_text = []
    for (bbox, data, pro) in result:
        extracted_text.append(data)
        print(data)
    # extracted_text = pytesseract.image_to_string(image)
    # print(extracted_text)
    extracted_text = " ".join(extracted_text)
    # Extract NIN (11 digits)
    nin_no = re.search(r'NIN:?\s*(\d{11})', extracted_text, re.IGNORECASE)
    if nin_no:
        nin_data["NIN"] = nin_no.group(1)
    
    # Extract First Name - handle both formats
    first_name = re.search(r'First\s*Na[mr][eo][:.]?\s*([A-Z]+)', extracted_text, re.IGNORECASE)
    if first_name:
        nin_data["First Name"] = first_name.group(1)
    
    # Extract Middle Name - handle both formats
    middle_name = re.search(r'Middle\s*Name[:.]?\s*([A-Z]+)', extracted_text, re.IGNORECASE)
    if middle_name:
        nin_data["Middle Name"] = middle_name.group(1)
    
    # Extract Surname/Last Name - handle multiple formats
    surname_patterns = [
        r'Su[mr]name[:.]?\s*([A-Z]+)',             # Basic "Surname: NAME" format
        r'Tracking ID:?\s*\S+\s+([A-Z]+)',         # Name after tracking ID
        r'(?:Su[mr]name|Surname)[:.]?\s*([A-Z]+)', # Explicit variants
    ]
    
    for pattern in surname_patterns:
        surname_match = re.search(pattern, extracted_text, re.IGNORECASE)
        if surname_match:
            nin_data["Last Name"] = surname_match.group(1)
            break
    
    # Extract Gender - handle both formats
    gender = re.search(r'Gender[:.]?\s*([MF])', extracted_text, re.IGNORECASE)
    if gender:
        nin_data["Gender"] = gender.group(1)
    
    # Extract Address - handle multiple formats
    address_patterns = [
        r'([0-9]+\s+[A-Z]+\s+STREET)',                       # Format like "7 OHIA STREET"
        r'(BESIDE\s+[A-Z\s]+(?:CHURCH|ROAD|STREET|AVENUE))', # Format like "BESIDE EMMANUEL BAPTIST CHURCH"
        r'((?:NO\.?|NO)?\s*\d+\s+[A-Z\s]+(?:STREET|ROAD|AVE))', # House number formats
    ]
    
    for pattern in address_patterns:
        address_match = re.search(pattern, extracted_text, re.IGNORECASE)
        if address_match:
            nin_data["Address"] = address_match.group(1)
            break
    
    # For multi-line addresses (like in your second example)
    if "Address" not in nin_data:
        # Look for text between surname and first name that might be address
        multi_line_address = re.search(r'(?:Su[mr]name|Surname)[:.]?\s+[A-Z]+\s+(.*?)\s+First\s*Na[mr][eo]', 
                                    extracted_text, re.IGNORECASE | re.DOTALL)
        if multi_line_address:
            address_text = multi_line_address.group(1).strip()
            # Clean up multi-line address
            address_text = re.sub(r'\s+', ' ', address_text)
            nin_data["Address"] = address_text
    
    return nin_data
def process_passport(image):

    passport_data = {}
    
    extracted_text = pytesseract.image_to_string(image)

    passport_no = re.search(r'[A-Z]\d{8}', extracted_text)
    if passport_no:
        passport_data["Passport No"] = passport_no.group()
    country_code = re.search(r'[A-Z]{3}', extracted_text)
    if country_code:
        passport_data["Country Code"] = country_code.group()
    given_name = re.search(r'(?:GIVEN NAMES)[:\s]+([A-Z\s]+)', extracted_text, re.IGNORECASE)
    if given_name:
        passport_data["Given Name"] = given_name.group(1).strip()
    surname = re.search(r'(?:SURNAME)[:\s]+([A-Z]+)', extracted_text, re.IGNORECASE)
    if surname:
        passport_data["Surname"] = surname.group(1)
    nationality = re.search(r'NATIONALITY[:\s]+([A-Z]+)', extracted_text, re.IGNORECASE)
    if nationality:
        passport_data["Nationality"] = nationality.group(1)
    date_of_birth= re.search(r'DATE OF BIRTH[:\s]+(\d{2}\s+[A-Z]{3}\s+\d{4})', extracted_text, re.IGNORECASE)
    if date_of_birth:
        passport_data["Date of Birth"] = date_of_birth.group(1)
    place_of_birth= re.search(r'PLACE OF BIRTH[:\s]+([A-Z\s]+)', extracted_text, re.IGNORECASE)
    if place_of_birth:
        passport_data["Place of Birth"] = place_of_birth.group(1).strip()
    sex = re.search(r'SEX[:\s]+([MF])', extracted_text, re.IGNORECASE)
    if sex:
        passport_data["Sex"] = sex.group(1)
    date_of_issue = re.search(r'DATE OF ISSUE[:\s]+(\d{2}\s+[A-Z]{3}\s+\d{4})', extracted_text, re.IGNORECASE)
    if date_of_issue:
        passport_data["Date of Issue"] = date_of_issue.group(1)
    date_of_expiry = re.search(r'DATE OF EXPIRY[:\s]+(\d{2}\s+[A-Z]{3}\s+\d{4})', extracted_text, re.IGNORECASE)
    if date_of_expiry:
        passport_data["Date of Expiry"] = date_of_expiry.group(1)
    
    return passport_data



def main():
    
    if "ocr_type" not in st.session_state:
        st.session_state.ocr_type = None

    if "image" not in st.session_state:
        st.session_state.image = None
    
    if "upload" not in st.session_state:
        st.session_state.upload = False
    
    if "scan" not in st.session_state:
        st.session_state.scan = False

    # If no OCR type is selected, show options
    if not st.session_state.ocr_type:
        st.title("Welcome to Bolu's OCR Implementation")

        # OCR selection dropdown
        ocr_options = ["Select an Option", "Upload Document", "Scan Document"]
        ocr_option = st.selectbox("Select OCR Option", ocr_options)

        if ocr_option != "Select an Option":  # If user selects an option
            st.session_state.ocr_type = ocr_option  # Store the selected option
            
            if ocr_option == "Upload Document":
                st.session_state.upload = True
                st.session_state.scan = False
            
            if ocr_option == "Scan Document":
                st.session_state.upload = False
                st.session_state.scan = True
            
            st.rerun()  # Refresh the page to apply selection

    # If OCR type is already selected, display it
    else:
        st.title(f"Welcome to Bolu's {st.session_state.ocr_type} OCR Implementation")
        
        image_options = ["Select Image Type","Passport", "NIN"]
        image_option = st.selectbox("Select Image Type", image_options)

        if image_option != "Select Image Type":
            st.session_state.image = image_option
            st.success(f"Selected Image Type: {image_option}")
        
            if st.session_state.upload:
                upload_image = st.file_uploader("Upload an Image")
                if upload_image:
                    st.image(upload_image, caption="Uploaded Image", use_container_width=True)
                    if st.session_state.image == "Passport":
                        response = process_image(upload_image)
                        final_response = process_passport(response)
                        st.write(final_response)
                    elif st.session_state.image == "NIN":
                        response = process_image(upload_image)
                        final_response = process_nin(response)
                        st.write(final_response)
            
            elif st.session_state.scan:
                scan_image  = st.camera_input("take a picture")
                if scan_image:
                    st.image(scan_image, caption="Scanned Image", use_container_width=True)
                    if st.session_state.image == "Passport":
                        response = process_image(scan_image)
                        final_response = process_passport(response)
                        st.write(final_response)
                    elif st.session_state.image == "NIN":
                        response = process_image(scan_image)
                        final_response = process_nin(response)
                        st.write(final_response)




if __name__ == "__main__":
    main()
