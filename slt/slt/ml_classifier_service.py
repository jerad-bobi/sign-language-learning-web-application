from __future__ import annotations

from accounts.models import SkeletalSignSample
from .skeletal_classifier_service import _build_signature, normalize_landmarks

_ML_CACHE: dict = {'signature': None, 'model': None}

_MIN_CLASSES = 2
_MIN_CANDIDATE_CONFIDENCE = 0.20
_CANDIDATE_CONFIDENCE_RATIO = 0.55
_MAX_CANDIDATES = 3


def _train_model() -> dict | None:
    try:
        import numpy as np
        from sklearn.neural_network import MLPClassifier
        from sklearn.preprocessing import LabelEncoder
    except ImportError:
        return None

    sign_vectors: dict[str, list[list[float]]] = {}

    for sample in SkeletalSignSample.objects.values('sign_folder', 'feature_vector').iterator():
        sign_name = str(sample.get('sign_folder', '')).strip()
        fv = sample.get('feature_vector')
        if not sign_name or not isinstance(fv, list) or not fv:
            continue
        try:
            sign_vectors.setdefault(sign_name, []).append([float(v) for v in fv])
        except (TypeError, ValueError):
            continue

    if len(sign_vectors) < _MIN_CLASSES:
        return None

    X: list[list[float]] = []
    y: list[str] = []

    for sign_name, vectors in sign_vectors.items():
        for vec in vectors:
            X.append(vec)
            y.append(sign_name)
            # Mirror augmentation: flip x-coordinates to handle handedness variation
            mirrored = vec.copy()
            for i in range(0, len(mirrored), 2):
                mirrored[i] = -mirrored[i]
            X.append(mirrored)
            y.append(sign_name)

    le = LabelEncoder()
    y_enc = le.fit_transform(y)

    clf = MLPClassifier(
        hidden_layer_sizes=(128, 64),
        activation='relu',
        max_iter=300,
        random_state=42,
    )
    clf.fit(np.array(X, dtype=float), y_enc)

    return {
        'clf': clf,
        'le': le,
        'classes': len(sign_vectors),
        'samples': sum(len(v) for v in sign_vectors.values()),
    }


def _get_model() -> dict | None:
    sig = _build_signature()
    if _ML_CACHE['signature'] == sig and _ML_CACHE['model'] is not None:
        return _ML_CACHE['model']
    model = _train_model()
    _ML_CACHE['signature'] = sig
    _ML_CACHE['model'] = model
    return model


def predict_sign_ml(landmarks: list[dict]) -> dict:
    fv = normalize_landmarks(landmarks)
    if fv is None:
        return {'ok': False, 'error': 'Invalid landmarks.'}

    model = _get_model()
    if model is None:
        return {
            'ok': False,
            'error': 'ML model requires at least 2 sign classes with captured samples.',
            'classes': 0,
            'samples': 0,
        }

    try:
        import numpy as np

        clf = model['clf']
        le = model['le']

        proba = clf.predict_proba(np.array([fv], dtype=float))[0]
        scored = sorted(
            [{'sign': str(le.classes_[i]), 'confidence': float(proba[i])} for i in range(len(le.classes_))],
            key=lambda x: x['confidence'],
            reverse=True,
        )

        best_conf = scored[0]['confidence']

        candidates = [
            {
                'sign': c['sign'],
                'distance': 0.0,
                'confidence': c['confidence'],
                'confidence_percent': round(c['confidence'] * 100),
                'samples': 0,
            }
            for c in scored
            if c['confidence'] >= _MIN_CANDIDATE_CONFIDENCE
            and c['confidence'] >= best_conf * _CANDIDATE_CONFIDENCE_RATIO
        ][:_MAX_CANDIDATES]

        if not candidates:
            candidates = [{
                'sign': scored[0]['sign'],
                'distance': 0.0,
                'confidence': best_conf,
                'confidence_percent': round(best_conf * 100),
                'samples': 0,
            }]

        return {
            'ok': True,
            'predicted_sign': scored[0]['sign'],
            'confidence': best_conf,
            'confidence_percent': round(best_conf * 100),
            'distance': 0.0,
            'classes': model['classes'],
            'samples': model['samples'],
            'matched_samples': 0,
            'candidates': candidates,
        }

    except Exception:
        return {'ok': False, 'error': 'ML prediction failed.', 'classes': 0, 'samples': 0}
