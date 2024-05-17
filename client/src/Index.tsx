import React from "react";
import { AuthProvider } from "./context/auth";
import App from "./App";
import { FxnProvider } from "./context/fxns";

export default function Index() {
    return (
        <AuthProvider>
            <FxnProvider>
                <App />
            </FxnProvider>
        </AuthProvider>
    );
}