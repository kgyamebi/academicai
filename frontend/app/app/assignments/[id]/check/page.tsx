"use client";

import { useParams } from "next/navigation";
import CheckPage from "@/app/check/page";

export default function AssignmentCheckPage() {
  useParams();
  return <CheckPage />;
}
