import JobListingHunter from "./pages/JobListingHunter";
import ProfileCreation from "./pages/ProfileCreation";
import JobMatcher from "./pages/JobMatcher";

export type Page = "hunter" | "profile" | "matcher";

export default function DashboardRouter({ page }: { page: Page }) {
  switch (page) {
    case "profile":
      return <ProfileCreation />;
    case "matcher":
      return <JobMatcher />;
    default:
      return <JobListingHunter />;
  }
}
