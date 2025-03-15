from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from application.extensions import db

from application.services.concept_service import ConceptService
from application.services.lexical_service import LexicalService
from application.services.user_service import UserService
import smtplib
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from application.models.concept_submissions import ConceptSubmission
from application.models.concept_dictionary_model import ConceptDictionary
from flask import jsonify, request
from sqlalchemy.orm import sessionmaker
from application.services.measure_time import measure_response_time



concept_blueprint = Blueprint('concepts', __name__)

@concept_blueprint.route('/getconcepts/<string:hindi_label>', methods=['GET'])
@jwt_required()
@measure_response_time
def get_concepts_by_hindi_label(hindi_label):
    # Fetch concepts by hindi_label
    concepts = ConceptService.get_concepts_by_hindi_label(hindi_label)
    if concepts:
        filtered_concepts = {concept.hindi_label: {
                                  "english_label": concept.english_label,
                                  "concept_id": concept.concept_id
                              } 
                             for concept in concepts 
                             if concept.hindi_label == hindi_label or concept.hindi_label.startswith(f"{hindi_label}_")}
        
        if filtered_concepts:
            return jsonify({"concepts": filtered_concepts, "option": "list_found"}), 200

    # Option when no concepts are found
    return jsonify({"message": "No concepts found for the given hindi_label", "option": "other"}), 404


@concept_blueprint.route('/getconceptss/<string:english_label>', methods=['GET'])
def get_concepts_by_english_label(english_label):
    """
    Validate the English label and suggest the next available label if it exists.
    """
    try:
        # Extract the base name (e.g., 'lesson' from 'lesson_1')
        base_label = english_label.split('_')[0]
        
        # Fetch all English labels starting with the base label
        existing_labels = ConceptService.get_concepts_by_english_label(base_label)
        
        # Log existing labels to check if they are fetched correctly
        print(f"Existing labels: {existing_labels}")

        # Regex to extract numeric parts from labels like lesson_1, lesson_2, etc.
        numeric_label_pattern = re.compile(rf"^{base_label}_(\d+)$")

        # Find the numbers from the existing labels
        existing_numbers = []
        for label in existing_labels:
            match = numeric_label_pattern.match(label)
            if match:
                existing_numbers.append(int(match.group(1)))

        # Suggest the next label by incrementing the highest existing number by 1
        if existing_numbers:
            max_number = max(existing_numbers)
            next_label = f"{base_label}_{max_number + 1}"
        else:
            # If no labels exist, suggest the first label
            next_label = f"{base_label}_1"

        # Check if the exact label exists
        if english_label in existing_labels:
            return jsonify({
                'option': 'found',
                'message': f"The English label '{english_label}' already exists.",
                'suggested_label': next_label
            }), 200
        else:
            return jsonify({
                'option': 'not_found',
                'message': f"The English label '{english_label}' does not exist.",
                'suggested_label': next_label
            }), 200

    except Exception as e:
        # Handle unexpected errors
        return jsonify({'error': f"An error occurred: {str(e)}"}), 500

    



# List of recipient emails (adjust as needed)


# Fetch emails dynamically based on role
def get_recipient_emails():
    try:
        # Fetch users with the role 'dictionaryValidator'
        recipients = UserService.get_users_by_role('dictionaryValidator')
        print(recipients);
        return [user.email for user in recipients]
    except Exception as e:
        print(f"Error fetching recipients: {e}")
        return []

# Counter to track the next recipient (this needs to persist across requests)
current_recipient_index = 0

@concept_blueprint.route('/submit_concept', methods=['POST'])
def submit_concept():
    global current_recipient_index  # Use the global counter to track the recipient index
    data = request.get_json()

    # Retrieve the user ID
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400

    # Fetch user details using user_id
    user = UserService.get_user_by_id(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    from_email = user.email  # Use the user's email as the "from" address

    # Retrieve the concepts
    concept = data.get('concept', {})
    hindi_concept = concept.get('hindi', '')
    english_concept = concept.get('english', '')
    concept_id = data.get('indexes', [])[0]  # Assuming only one concept ID is sent
    sentence_data = data.get('subSegment', '')  # Subsegment data with sentence info

    # Extracting sentence ID and text (Hindi sentence) from subSegment
    try:
        sentence_id, hindi_sentence = sentence_data.split(' : ', 1)
    except ValueError:
        sentence_id, hindi_sentence = '', sentence_data  # Fallback if format is incorrect

    # Retrieve the English sentence from the request data
    english_sentence = data.get('english_sentence', '')
    if not english_sentence:
        return jsonify({"error": "English sentence is required"}), 400

    # Debug: Print received data (remove in production)
    print(f"Received Hindi Concept: {hindi_concept}")
    print(f"Received English Concept: {english_concept}")
    print(f"Concept ID: {concept_id}")
    print(f"Sentence ID: {sentence_id}")
    print(f"Hindi Sentence: {hindi_sentence}")
    print(f"English Sentence: {english_sentence}")
    print(f"From Email (User): {from_email}")

    # Prepare the email content
    subject = "New Concept Request"
    body = (
        f"Dear Team,\n\n"
        f"A new concept has been submitted for review:\n\n"
        f"Concept Details:\n"
        f"- **Hindi Concept**: {hindi_concept}\n"
        f"- **English Concept**: {english_concept}\n"
        f"- **Concept ID**: {concept_id}\n\n"
        f"Sentence Details:\n"
        f"- **Sentence ID**: {sentence_id}\n"
        f"- **Hindi Sentence**: {hindi_sentence}\n"
        f"- **English Sentence**: {english_sentence}\n\n"
        f"Please review the submission at your earliest convenience.\n\n"
        f"Best regards,\n"
        f"Your Automated Concept Submission System"
    )

    # Fetch recipient emails dynamically
    recipient_emails = get_recipient_emails()
    if not recipient_emails:
        return jsonify({"error": "No recipients found with the role 'dictionary validator'."}), 500

    # Get the next recipient email
    recipient_email = recipient_emails[current_recipient_index]
    current_recipient_index = (current_recipient_index + 1) % len(recipient_emails)  # Rotate index

    # Send email using the user's email as the "from" address
    send_email(subject, body, recipient_email, from_email=from_email)
    try:
        # Create a new ConceptSubmission instance
        new_submission = ConceptSubmission(
            user_id=user_id,
            from_email=from_email,
            to_email=recipient_email,
            hindi_concept=hindi_concept,
            english_concept=english_concept,
            concept_id=concept_id,
            sentence_id=sentence_id,
            sentence=hindi_sentence,  # Save the Hindi sentence
            english_sentence=english_sentence  # Save the English sentence
        )
        # Add the new submission to the session and commit it
        db.session.add(new_submission)
        db.session.commit()

        print(f"Submission data saved to the database.")
    except Exception as e:
        print(f"Error occurred: {e}") 
        return jsonify({"error": f"Failed to save submission to database: {str(e)}"}), 500

    return jsonify({"message": f"Concept submitted and email sent to {recipient_email}."}), 200



    # Send email
   

SMTP_SERVER = 'smtp.gmail.com'  # e.g., Gmail SMTP server
SMTP_PORT = 587  # SMTP port for STARTTLS
SENDER_EMAIL = 'swethapoppoppu@gmail.com'
SENDER_PASSWORD = 'ufec wkhp syss ynqa'  # Make sure this is securely handled



def send_email(subject, body, to_email, from_email=None):
    try:
        # Set up the email server
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()  # Start TLS encryption
        server.login(SENDER_EMAIL, SENDER_PASSWORD)

        # Determine the "From" address
        sender_email = from_email if from_email else SENDER_EMAIL

        # Create the email with UTF-8 headers and body
        msg = MIMEMultipart()
        msg['From'] = sender_email  # Use provided "from_email" if available
        msg['To'] = to_email
        msg['Subject'] = subject

        # Attach the body with UTF-8 encoding
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        # Ensure UTF-8 for all headers
        msg_str = msg.as_string()
        msg_bytes = msg_str.encode('utf-8')  # Encode the whole message as UTF-8

        # Send the email
        server.sendmail(sender_email, to_email, msg_bytes)
        server.quit()

        print(f"Email sent successfully from {sender_email} to {to_email}.")
    except Exception as e:
        print(f"Failed to send email: {e}")



@concept_blueprint.route('/get_req', methods=['GET'])
@jwt_required()  # Ensures the request is authenticated
@measure_response_time
def get_concepts():
    try:
        # Extract the 'user_id' from query parameters
        print("inside")
        user_id = request.args.get('user_id')  # Get the user_id from the URL query parameter
        if not user_id:
            return jsonify({"error": "User ID is required"}), 400
        
        print("outside")

        # Get the user details based on user_id
        user = UserService.get_user_by_id(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        current_user_email = user.email  # Use the user's email as the "from" address
        
        print(f"User Email: {current_user_email}")
        
        # Filter the data based on the user's email
        submissions = ConceptSubmission.query.filter(
            (ConceptSubmission.to_email == current_user_email)
        ).all()

        if not submissions:
            return jsonify({"error": "No data found"}), 404

        # Refresh each submission object individually
        for submission in submissions:
            db.session.refresh(submission)

        # Format the response data
        response_data = [
            {
                'Temp_Id': submission.id,
                'sentence_id': submission.sentence_id,
                'hindi_sentence': submission.sentence,  # Assuming this is the Hindi sentence field
                'english_sentence': submission.english_sentence,  # Assuming this is the English sentence field
                'concept_id': submission.concept_id,
                'hindi_label': submission.hindi_concept,  # Updated Hindi label field
                'english_label': submission.english_concept,  # Updated English label field
            }
            for submission in submissions
        ]

        # Log the response data for debugging (optional)
        print(f"Fetched concepts for User ID {user_id}: {response_data}")

        return jsonify(response_data), 200
    
    except Exception as e:
        print(f"Error fetching concepts: {str(e)}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500
    


@concept_blueprint.route('/update_concept/<temp_id>', methods=['PUT'])
@jwt_required()
@measure_response_time
def update_concept(temp_id):
    try:
        # Log the temp_id from the URL for debugging
        print(f"Updating concept with Temp_Id: {temp_id}")

        # Get JSON data from the request body
        data = request.get_json()

        # Debugging: Log the incoming JSON data
        print(f"Received data: {data}")

        # Extract fields from the incoming JSON
        hindi_concept = data.get('hindi_label')  # Adjusted to match frontend field names
        english_concept = data.get('english_label')  # Adjusted to match frontend field names

        # Check if required fields are present
        if not hindi_concept or not english_concept:
            print("Error: Missing required fields")
            return jsonify({"error": "hindi_label and english_label are required"}), 400

        # Log the extracted values for debugging
        print(f"Hindi Concept: {hindi_concept}")
        print(f"English Concept: {english_concept}")

        # Step 1: Query the database for the concept using temp_id
        concept = ConceptSubmission.query.filter_by(id=temp_id).first()

        if not concept:
            print(f"Error: No concept found with Temp_Id: {temp_id}")
            return jsonify({"error": "Concept not found"}), 404

        # Step 2: Update only the fields that need to be changed
        concept.hindi_concept = hindi_concept
        concept.english_concept = english_concept

        # Log before commit
        print(f"Before commit: Hindi Concept: {concept.hindi_concept}, English Concept: {concept.english_concept}")

        # Step 3: Commit the changes to the database
        try:
            db.session.commit()
            print(f"Commit successful: Hindi Concept: {concept.hindi_concept}, English Concept: {concept.english_concept}")
        except Exception as e:
            db.session.rollback()  # Rollback in case of failure
            print(f"Error during commit: {e}")
            return jsonify({"error": f"An error occurred while saving the data: {str(e)}"}), 500

        # Log after commit for debugging
        print(f"Updated Concept: Hindi Concept: {concept.hindi_concept}, English Concept: {concept.english_concept}")

        # Return a success response
        return jsonify({"message": "Concept updated successfully"}), 200

    except Exception as e:
        # Log the exception for debugging purposes
        print(f"Error: {str(e)}")
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500
    

@concept_blueprint.route('/reject/<temp_id>', methods=['DELETE'])
@jwt_required()
@measure_response_time
def reject_concept(temp_id):
    try:
        # Step 1: Find the concept to reject
        concept = ConceptSubmission.query.filter_by(id=temp_id).first()

        if not concept:
            return jsonify({"error": "Concept not found"}), 404

        # Step 2: Send an email to the user notifying them of rejection
        from_email = concept.from_email  # Get the user's email from the database
        subject = "Your concept was rejected"
        body = "We regret to inform you that your concept submission has been rejected."

        # Send the rejection email using your send_email function
        send_email(subject, body, from_email)

        # Step 3: Delete the concept from the database
        db.session.delete(concept)
        db.session.commit()

        # Step 4: Return success response
        return jsonify({"message": "Concept rejected successfully and email sent."}), 200

    except Exception as e:
        # Handle any exceptions and rollback the transaction if needed
        db.session.rollback()
        print(f"Error during concept rejection: {str(e)}")




@concept_blueprint.route('/accept_and_store/<temp_id>', methods=['POST'])
@jwt_required()
@measure_response_time
def accept_and_store(temp_id):
    try:
        # Fetch the concept using temp_id from the ConceptSubmission table
        concept = ConceptSubmission.query.filter_by(id=temp_id).first()

        if not concept:
            return jsonify({"error": "Concept not found"}), 404

        # Extract required fields for storage
        hindi_label = concept.hindi_concept
        english_label = concept.english_concept
        concept_label = hindi_label  # Use hindi_label as the default for concept_label
        from_email = concept.from_email  # Email to send the notification

        # Create a new entry in ConceptDictionary, skipping mrsc and sanskrit_label
        new_concept = ConceptDictionary(
            concept_label=concept_label,
            hindi_label=hindi_label,
            english_label=english_label
        )

        # Add the new concept to the database and commit the changes
        db.session.add(new_concept)
        db.session.commit()

        # Delete the entry from the ConceptSubmission table after successful insertion
        db.session.delete(concept)
        db.session.commit()

        # Send an email notification to the user
        subject = "Your Concept Has Been Accepted"
        body = f"Hello, your concept with the Hindi label '{hindi_label}' and English label '{english_label}' has been accepted."
        send_email(subject, body, to_email=from_email)

        # Return a success response
        return jsonify({"message": "Concept accepted and stored successfully"}), 200

    except Exception as e:
        # Rollback the database transaction in case of an error
        db.session.rollback()
        print(f"Error during accept_and_store: {str(e)}")
        return jsonify({"error": "An unexpected error occurred while storing the concept"}), 500
