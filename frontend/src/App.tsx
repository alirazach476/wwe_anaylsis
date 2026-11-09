import { Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import Overview from "./pages/Overview";
import Wrestlers from "./pages/Wrestlers";
import WrestlerDetail from "./pages/WrestlerDetail";
import Events from "./pages/Events";
import EventDetail from "./pages/EventDetail";
import EventSeries from "./pages/EventSeries";
import Matches from "./pages/Matches";
import Championships from "./pages/Championships";
import Rumble from "./pages/Rumble";
import Mitb from "./pages/Mitb";
import Survivor from "./pages/Survivor";
import GlobalPage from "./pages/GlobalPage";
import MlPage from "./pages/MlPage";
import Timeline from "./pages/Timeline";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Overview />} />
        <Route path="/wrestlers" element={<Wrestlers />} />
        <Route path="/wrestlers/:wrestlerId" element={<WrestlerDetail />} />
        <Route path="/events" element={<Events />} />
        <Route path="/events/:eventId" element={<EventDetail />} />
        <Route path="/series/:seriesSlug" element={<EventSeries />} />
        <Route path="/matches" element={<Matches />} />
        <Route path="/championships" element={<Championships />} />
        <Route path="/rumble" element={<Rumble />} />
        <Route path="/mitb" element={<Mitb />} />
        <Route path="/survivor" element={<Survivor />} />
        <Route path="/global" element={<GlobalPage />} />
        <Route path="/ml" element={<MlPage />} />
        <Route path="/timeline" element={<Timeline />} />
      </Route>
    </Routes>
  );
}
