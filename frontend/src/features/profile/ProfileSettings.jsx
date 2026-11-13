import { Link } from "react-router-dom";

import ErrorState from "../../components/common/ErrorState/ErrorState";
import Spinner from "../../components/common/Spinner/Spinner";
import AllergiesForm from "./components/AllergiesForm";
import PreferencesForm from "./components/PreferencesForm";
import ProfileForm from "./components/ProfileForm";
import useProfileSettings from "./hooks/useProfileSettings";

import "./ProfileSettings.css";

/**
 * Profile, cuisine/diet preferences and allergies for the signed-in user.
 */
export default function ProfileSettings() {
    const settings = useProfileSettings();

    if (settings.status === "loading") {
        return (
            <div className="profile-settings__center">
                <Spinner label="Loading your profile..." />
            </div>
        );
    }

    if (settings.status === "error") {
        const { message, authRequired } = settings.loadError;

        return authRequired ? (
            <div className="profile-settings__center">
                <ErrorState
                    title="Sign in required"
                    description={message}
                />
                <Link to="/login">Go to sign in</Link>
            </div>
        ) : (
            <ErrorState
                title="Unable to load your profile"
                description={message}
                onRetry={settings.reload}
            />
        );
    }

    return (
        <div className="profile-settings">
            <ProfileForm user={settings.user} onSave={settings.saveProfile} />

            <PreferencesForm
                tags={settings.tags}
                savedIds={settings.preferenceIds}
                onSave={settings.savePreferences}
            />

            <AllergiesForm
                allergens={settings.allergens}
                savedIds={settings.allergyIds}
                onSave={settings.saveAllergies}
            />
        </div>
    );
}
