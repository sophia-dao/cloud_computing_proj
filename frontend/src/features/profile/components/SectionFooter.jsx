import Button from "../../../components/common/Button/Button";

export default function SectionFooter({ label, dirty, saving, error }) {
    return (
        <div className="profile-settings__footer">
            <Button type="submit" disabled={!dirty || saving}>
                {saving ? "Saving..." : label}
            </Button>

            {error && (
                <p className="profile-settings__error" role="alert">
                    {error}
                </p>
            )}
        </div>
    );
}
