from application.extensions import db
from application.models.generation_model import Generation

class GenerationService:
    @staticmethod
    def get_generated_text_by_segment_id(segment_id, chapter_id):
        result = (
            db.session.query(Generation.generated_text)
            .filter(
                Generation.segment_id == segment_id,
                Generation.chapter_id == chapter_id
            )
            .first()
        )
        
        if result:
            return result.generated_text
        return None

    @staticmethod
    def get_generated_text_as_string(segment_id):
        # Query the generation by segment_id
        generation = Generation.query.filter_by(segment_id=segment_id).first()
        if not generation:
            return None

        # Extract the generated text
        generated_text = generation.generated_text

        # Create a formatted output
        output = f"<segment_id={generation.segment_index}>\n"
        output += f"#{generation.generated_text}\n"
        output += f"</segment_id>"

        return output
    
    @staticmethod
    def get_all_generated_texts_by_chapter(chapter_id):
        # Query all generations by chapter_id
        generations = Generation.query.filter_by(chapter_id=chapter_id).all()
        
        if not generations:
            return None

        # Build a list of formatted generated texts
        generated_texts = []
        for generation in generations:
            output = f"<segment_id={generation.segment_index}>\n"
            output += f"#{generation.generated_text}\n"
            output += f"</segment_id>\n"
            generated_texts.append(output)

        return generated_texts
