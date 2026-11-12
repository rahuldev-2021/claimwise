import { Navigate, useParams } from "react-router-dom";
import { ClaimDetailPage } from "./ClaimDetailPage";

/** Prevents `claims/:claimId` from treating `new` as a claim id. */
export function ClaimDetailRoute() {
  const { claimId = "" } = useParams();
  if (claimId.toLowerCase() === "new") {
    return <Navigate to="/claims/new" replace />;
  }
  return <ClaimDetailPage />;
}
