from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from typing import Optional, List
from observability import run_onboarding
from data_loader import load_onboarding_requests

app = FastAPI(title="HR Onboarding Agent API")

class OnboardingRequest(BaseModel):
    request_id: str
    employee_email: str
    department: str
    role: str
    location: str
    requested_systems: List[str]
    user_query: Optional[str] = None

@app.post("/process_request")
def process_request(request: OnboardingRequest):
    try:
        req_dict = request.model_dump()
        result = run_onboarding(req_dict, query=request.user_query)
        if hasattr(result, "model_dump"):
            res_dict = result.model_dump()
        else:
            res_dict = dict(result)
        return jsonable_encoder({"status": "success", "result": res_dict})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/requests/batch")
def process_batch():
    try:
        requests = load_onboarding_requests()
        results = []
        for req in requests:
            res = run_onboarding(req)
            if hasattr(res, "model_dump"):
                results.append(res.model_dump())
            else:
                results.append(dict(res))
        return jsonable_encoder({"processed": len(requests), "results": results})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "healthy"}
