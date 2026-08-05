from sklearn.ensemble import RandomForestClassifier
import numpy as np

class IntentClassifier:
    def __init__(self):
        # Modelo simulado com sklearn
        self.clf = RandomForestClassifier(n_estimators=10)
        # Treinamento dummy
        X_dummy = np.random.rand(10, 5)
        y_dummy = np.random.randint(0, 2, 10)
        self.clf.fit(X_dummy, y_dummy)
        
    def predict_intent(self, state_features: np.ndarray) -> int:
        if len(state_features) != 5:
            # mock for dummy size
            state_features = np.zeros(5)
        return self.clf.predict([state_features])[0]
