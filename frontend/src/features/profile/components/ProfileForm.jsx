import { useState } from "react";

import FormCard from "../../../components/common/FormCard/FormCard";
import Input from "../../../components/common/Input/Input";
import useSaveState from "../hooks/useSaveState";
import SectionFooter from "./SectionFooter";

const MAX_NAME_LENGTH = 150;

function isHttpUrl(value) {
    try {
        const { protocol } = new URL(value);
        return protocol === "http:" || protocol === "https:";
    } catch {
        return false;
    }
}

export default function ProfileForm({ user, onSave }) {
    const savedName = user.display_name || "";
    const savedImage = user.profile_image || "";

    const [displayName, setDisplayName] = useState(savedName);
    const [profileImage, setProfileImage] = useState(savedImage);
    const [clientErrors, setClientErrors] = useState({});

    const save = useSaveState();

    const dirty = displayName !== savedName || profileImage !== savedImage;
    const errors = { ...save.fieldErrors, ...clientErrors };

    function handleSubmit(event) {
        event.preventDefault();

        const name = displayName.trim();
        const image = profileImage.trim();
        const nextErrors = {};

        if (name.length > MAX_NAME_LENGTH) {
            nextErrors.display_name =
                `Display name must be ${MAX_NAME_LENGTH} characters or fewer.`;
        }

        if (image && !isHttpUrl(image)) {
            nextErrors.profile_image = "Enter a valid http(s) image URL.";
        }

        setClientErrors(nextErrors);
        if (Object.keys(nextErrors).length > 0) return;

        setDisplayName(name);
        setProfileImage(image);

        save.run(
            () => onSave({ displayName: name, profileImage: image }),
            "Profile saved."
        );
    }

    return (
        <FormCard
            title="Profile"
            description="Your account details."
            onSubmit={handleSubmit}
            noValidate
            footer={
                <SectionFooter
                    label="Save profile"
                    dirty={dirty}
                    saving={save.saving}
                    error={save.status === "error" ? save.message : ""}
                />
            }
        >
            <Input
                label="Email"
                type="email"
                value={user.email || ""}
                readOnly
                helperText="Your email is managed by your sign-in account."
            />

            <Input
                label="Display name"
                value={displayName}
                maxLength={MAX_NAME_LENGTH}
                onChange={(event) => setDisplayName(event.target.value)}
                error={errors.display_name}
            />

            <Input
                label="Profile image URL"
                type="url"
                placeholder="https://..."
                value={profileImage}
                onChange={(event) => setProfileImage(event.target.value)}
                error={errors.profile_image}
            />
        </FormCard>
    );
}
