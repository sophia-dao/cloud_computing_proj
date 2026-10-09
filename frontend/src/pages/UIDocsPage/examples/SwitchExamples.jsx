
import { useState } from "react";
import Switch from "../../../components/common/Switch/Switch";

function SwitchExamples() {
    const [settings, setSettings] = useState({
        notifications: true,
        autoPreferences: false,
    });

    function handleChange(event) {
        const { name, checked } = event.target;

        setSettings((current) => ({
            ...current,
            [name]: checked,
        }));
    }

    return (
        <div className="ui-docs__example-stack">
            <h4>Application Settings</h4>

            <Switch
                name="notifications"
                label="Enable Notifications"
                description="Receive updates about saved recipes."
                checked={settings.notifications}
                onChange={handleChange}
            />

            <Switch
                name="autoPreferences"
                label="Apply Saved Preferences"
                description="Automatically use your saved dietary preferences."
                checked={settings.autoPreferences}
                onChange={handleChange}
            />

            <h4>Disabled</h4>

            <Switch
                label="Unavailable Setting"
                disabled
            />

            <pre>{JSON.stringify(settings, null, 2)}</pre>
        </div>
    );
}

export default SwitchExamples;
