import { useState } from "react";
import { Link } from "react-router-dom";

import Card from "../../../components/common/Card/Card";

import "./UserSummary.css";

export default function UserSummary({ user }) {
    const [failedImage, setFailedImage] = useState(null);

    const name =
        user.display_name?.trim() || user.email?.split("@")[0] || "there";
    const showImage = Boolean(user.profile_image) && failedImage !== user.profile_image;

    return (
        <Card>
            <div className="user-summary">
                {showImage ? (
                    <img
                        className="user-summary__avatar"
                        src={user.profile_image}
                        alt=""
                        onError={() => setFailedImage(user.profile_image)}
                    />
                ) : (
                    <span
                        className="user-summary__avatar user-summary__avatar--initial"
                        aria-hidden="true"
                    >
                        {name.charAt(0).toUpperCase()}
                    </span>
                )}

                <div className="user-summary__text">
                    <h2 className="user-summary__name">Hi, {name}</h2>
                    <p className="user-summary__email">{user.email}</p>
                </div>

                <Link
                    to="/profile"
                    className="user-summary__action ui-button ui-button--secondary ui-button--md"
                >
                    Edit profile
                </Link>
            </div>
        </Card>
    );
}
