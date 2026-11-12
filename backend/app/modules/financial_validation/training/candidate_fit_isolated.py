"""Process-isolated model.fit for hard timeouts (no partial parent-side artifacts)."""

from __future__ import annotations

import multiprocessing as mp
from pathlib import Path
from typing import Any


def _fit_worker(
    candidate: str,
    random_seed: int,
    x_path: str,
    y_path: str,
    out_path: str,
    result_queue: mp.Queue,
) -> None:
    try:
        import joblib
        import numpy as np

        from app.modules.financial_validation.models.regressor_factory import create_regressor

        x = np.load(x_path)
        y = np.load(y_path)
        model = create_regressor(candidate, random_seed)
        model.fit(x, y)
        joblib.dump(model, out_path)
        result_queue.put({"status": "ok"})
    except Exception as exc:  # noqa: BLE001
        result_queue.put({"status": "error", "error": str(exc)})


def fit_regressor_in_subprocess(
    candidate: str,
    *,
    random_seed: int,
    x_matrix: Any,
    y_vector: Any,
    work_dir: Path,
    timeout_seconds: float | None,
) -> tuple[Any | None, dict[str, Any]]:
    """Fit in a child process; terminate hard on timeout. Returns (model, meta)."""
    import joblib
    import numpy as np

    work_dir.mkdir(parents=True, exist_ok=True)
    x_path = work_dir / "X.npy"
    y_path = work_dir / "y.npy"
    model_path = work_dir / "model.joblib"
    np.save(x_path, np.asarray(x_matrix))
    np.save(y_path, np.asarray(y_vector))

    ctx = mp.get_context("spawn")
    result_queue: mp.Queue = ctx.Queue()
    proc = ctx.Process(
        target=_fit_worker,
        args=(candidate, random_seed, str(x_path), str(y_path), str(model_path), result_queue),
        daemon=True,
    )
    proc.start()
    proc.join(timeout=timeout_seconds)

    meta: dict[str, Any] = {"candidate": candidate, "isolated_fit": True}
    if proc.is_alive():
        proc.terminate()
        proc.join(10)
        if proc.is_alive():
            proc.kill()
            proc.join(5)
        meta["status"] = "NOT COMPLETED"
        meta["reason"] = f"fit exceeded {timeout_seconds}s hard timeout (process terminated)"
        model_path.unlink(missing_ok=True)
        return None, meta

    if proc.exitcode != 0:
        meta["status"] = "FAIL"
        meta["reason"] = f"subprocess exit code {proc.exitcode}"
        model_path.unlink(missing_ok=True)
        return None, meta

    try:
        payload = result_queue.get_nowait()
    except Exception:
        payload = {"status": "error", "error": "no result from worker"}

    if payload.get("status") != "ok" or not model_path.is_file():
        meta["status"] = "FAIL"
        meta["reason"] = payload.get("error", "fit failed")
        model_path.unlink(missing_ok=True)
        return None, meta

    model = joblib.load(model_path)
    meta["status"] = "ok"
    return model, meta


def candidates_requiring_isolated_fit() -> set[str]:
    return {"gradient_boosting"}
