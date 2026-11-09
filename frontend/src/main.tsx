import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import { FilterProvider } from "./state/filters";
import { EventThemeProvider } from "./theme/EventThemeContext";
import { WrestlerIndexProvider } from "./state/WrestlerIndex";
import "./theme/tokens.css";
import "./theme/broadcast.css";
import "./styles.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <FilterProvider>
        <EventThemeProvider>
          <WrestlerIndexProvider>
            <App />
          </WrestlerIndexProvider>
        </EventThemeProvider>
      </FilterProvider>
    </BrowserRouter>
  </React.StrictMode>
);
