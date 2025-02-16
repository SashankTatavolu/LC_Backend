from application.extensions import db
from application.models.concept_dictionary_model import ConceptDictionary
from application.models.concept_submissions import ConceptSubmission

class ConceptService:
    @staticmethod
    def get_concepts_by_hindi_label(hindi_label):
        # Extracts the part before "_"
        prefix = hindi_label.split('_')[0]  
        return ConceptDictionary.query.filter(ConceptDictionary.hindi_label.like(f"{prefix}_%")).all()
    
 

    @staticmethod
    def get_concepts_by_english_label(english_label):
        """
        Fetch all English labels starting with the base label.
        Example: If `english_label` is "lesson", return ["lesson", "lesson_1", "lesson_2"].
        """
        base_label = english_label.split('_')[0]  # Extract the base part before '_'
        concepts = ConceptDictionary.query.filter(
            ConceptDictionary.english_label.like(f"{base_label}%")
        ).all()
        return [concept.english_label for concept in concepts]


 
   
    @staticmethod
    def get_next_available_english_label(base_label, existing_labels):
        """
        Generate the next available English label.
        Example: If `existing_labels` are ["lesson", "lesson_1", "lesson_2"], suggest "lesson_3".
        """
        # Remove duplicates from existing labels
        existing_labels = list(set(existing_labels))  # Convert to set to remove duplicates and back to list
        print(f"Existing labels (after removing duplicates): {existing_labels}")

        # Extract numbers from existing labels
        numbers = []
        for label in existing_labels:
            # Check if the label starts with the base label and has an underscore followed by digits
            if label.startswith(base_label + '_'):
                # Extract the number after the base label (e.g., lesson_1 -> 1)
                suffix = label[len(base_label) + 1:]  # Skip the base_label + underscore
                print(f"Processing label: {label}, extracted suffix: {suffix}")
                if suffix.isdigit():
                    numbers.append(int(suffix))

        print(f"Extracted numbers: {numbers}")

        # Suggest the next available number
        if numbers:
            next_number = max(numbers) + 1  # Get the next number after the maximum
            print(f"Max number found: {max(numbers)}, next suggested number: {next_number}")
        else:
            next_number = 1  # If no existing labels, start from 1
            print(f"No numbers found, starting from 1")

        # Return the next label suggestion
        suggested_label = f"{base_label}_{next_number}"
        print(f"Suggested next label: {suggested_label}")
        return suggested_label
    

    @staticmethod
    def update_concept(temp_id, hindi_label, english_label):
        try:
            # Query the database for the concept
            concept = ConceptSubmission.query.filter_by(id=temp_id).first()

            if not concept:
                raise ValueError(f"No concept found with Temp_Id: {temp_id}")

            # Update the concept labels
            concept.hindi_label = hindi_label
            concept.english_label = english_label

            # Commit the transaction
            db.session.commit()
            print(f"Concept with Temp_Id: {temp_id} updated successfully in the database.")
            
            # Refresh the concept from the database to ensure we get the latest values
            db.session.refresh(concept)
            print(f"Updated Concept after commit: {concept.hindi_label}, {concept.english_label}")
            
            return concept  # Return the updated concept object

        except Exception as e:
            db.session.rollback()
            print(f"Transaction rolled back. Error: {e}")
            raise Exception("Database transaction failed")






