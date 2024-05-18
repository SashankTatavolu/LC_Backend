from application.models.sentence_model import Sentence
from application.extensions import db

class SentenceService:
    @staticmethod
    def create_sentences(chapter_id, sentences_data):
        # This assumes a reset of index to 1 for every new upload
        new_sentences = []

        for index, text in enumerate(sentences_data, start=1):  # Start indexing from 1
            sentence = Sentence(
                chapter_id=chapter_id,
                sentence_index=index,
                text=text
            )
            new_sentences.append(sentence)

        db.session.bulk_save_objects(new_sentences)
        db.session.commit()
        return new_sentences
