from prance import ResolvingParser
from typing import List, Dict, Any

def parse_spec(spec_path: str) -> List[Dict[str, Any]]:
    #parser = ResolvingParser(spec_path)
    #parser = ResolvingParser("openapi.json", backend=None)
    parser = ResolvingParser(
        "openapi.json",
        backend="openapi-spec-validator",
        strict=False
    )
    spec = parser.specification
    endpoints = []

    for path, path_item in spec.get("paths", {}).items():
        for method, op in path_item.items():
            if method.upper() in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                endpoints.append({
                    "path": path,
                    "method": method.upper(),
                    "summary": op.get("summary", ""),
                    "parameters": op.get("parameters", []),
                    "requestBody": op.get("requestBody", {}),
                    "responses": op.get("responses", {})
                })
    return endpoints