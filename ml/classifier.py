"""
GeoMed Emergency Classifier (Graceful Degradation)
"""
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.naive_bayes import MultinomialNB
    import numpy as np
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


class EmergencyClassifier:
    def __init__(self):
        self.is_trained = False
        if not SKLEARN_AVAILABLE:
            return
            
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.clf = MultinomialNB()
        self._train_dummy_model()

    def _train_dummy_model(self):
        """Train a basic model on common campus incidents."""
        texts = [
            "chest pain heart attack breathing difficulty",
            "severe bleeding accident crash fracture",
            "fever headache cough weak",
            "sports injury twisted ankle sprain",
            "fainted unconscious collapsed",
            "routine checkup transfer to hospital"
        ]
        labels = ["critical", "critical", "urgent", "urgent", "critical", "routine"]
        
        X = self.vectorizer.fit_transform(texts)
        self.clf.fit(X, labels)
        self.is_trained = True

    def predict(self, symptoms_text):
        if not SKLEARN_AVAILABLE or not self.is_trained:
            return {"emergency_type": "unknown", "confidence": 0.0}
            
        X_new = self.vectorizer.transform([symptoms_text])
        pred = self.clf.predict(X_new)[0]
        
        # Get probability
        probs = self.clf.predict_proba(X_new)[0]
        confidence = float(np.max(probs))
        
        return {
            "emergency_type": pred,
            "confidence": round(confidence, 2)
        }


# Singleton instance
classifier = EmergencyClassifier()

def classify_emergency(text):
    return classifier.predict(text)
