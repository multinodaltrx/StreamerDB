import React from "react";
import ReactDOM from "react-dom/client";
import { MantineProvider, createTheme } from "@mantine/core";
import { Notifications } from "@mantine/notifications";
import "@mantine/core/styles.css";
import "@mantine/notifications/styles.css";
import App from "./App";

const theme = createTheme({
  primaryColor: "wine",
  colors: {
    wine: ["#fceef0", "#f3dade", "#e8b2bb", "#de8795", "#d56476", "#d04d62", "#ce4157", "#b63348", "#a32b3f", "#8e1f34"],
  },
  defaultRadius: "md",
  fontFamily: "Inter, system-ui, -apple-system, 'Segoe UI', sans-serif",
});

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <MantineProvider theme={theme} defaultColorScheme="auto">
      <Notifications position="bottom-center" limit={3} />
      <App />
    </MantineProvider>
  </React.StrictMode>,
);
