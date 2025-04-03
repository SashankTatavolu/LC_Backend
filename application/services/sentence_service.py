# from application.models.sentence_model import Sentence
# from application.extensions import db

# class SentenceService:
#     @staticmethod
#     def create_sentences(chapter_id, sentences_data):
#         # This assumes a reset of index to 1 for every new upload
#         new_sentences = []

#         for index, text in enumerate(sentences_data, start=1):  # Start indexing from 1
#             sentence = Sentence(
#                 chapter_id=chapter_id,
#                 sentence_index=index,
#                 text=text
#             )
#             new_sentences.append(sentence)

#         db.session.bulk_save_objects(new_sentences)
#         db.session.commit()
#         return new_sentences


from application.models.sentence_model import Sentence
from application.extensions import db

class SentenceService:
    @staticmethod
    def create_sentences(chapter_id, sentences_data):
        new_sentences = []

        for index, line in enumerate(sentences_data, start=1):
            print(f"Processing line {index}: {repr(line)}")  # Debugging

            line = line.strip()
            parts = line.split("\t")  # First try with tab

            if len(parts) != 2:
                parts = line.split(maxsplit=1)  # Retry with space if tab doesn't work

            if len(parts) != 2:
                print(f"Skipping malformed line: {repr(line)}")
                continue  # Skip malformed lines

            sentence_id, text = parts
            sentence = Sentence(
                chapter_id=chapter_id,
                sentence_index=index,
                sentence_id=sentence_id.strip(),
                text=text.strip()
            )
            new_sentences.append(sentence)

        if new_sentences:  # Avoid inserting empty data
            try:
                db.session.bulk_save_objects(new_sentences)
                db.session.commit()
                print(f"Total sentences inserted: {len(new_sentences)}")
            except Exception as e:
                db.session.rollback()
                print(f"Database error: {e}")
                return []  # Return empty list in case of failure

        return new_sentences  # Ensure a list is always returned


