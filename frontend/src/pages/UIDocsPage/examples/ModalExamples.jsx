
import { useState } from "react";

import Button from "../../../components/common/Button/Button";
import Input from "../../../components/common/Input/Input";
import Modal from "../../../components/common/Modal/Modal";

function ModalExamples() {
    const [basicOpen, setBasicOpen] = useState(false);
    const [confirmOpen, setConfirmOpen] = useState(false);
    const [formOpen, setFormOpen] = useState(false);
    const [ingredient, setIngredient] = useState("");

    function handleFormSubmit(event) {
        event.preventDefault();
        setFormOpen(false);
    }

    return (
        <div className="ui-docs__example-stack">
            <div className="ui-docs__example-row">
                <Button onClick={() => setBasicOpen(true)}>
                    Basic Modal
                </Button>

                <Button
                    variant="secondary"
                    onClick={() => setConfirmOpen(true)}
                >
                    Confirmation Modal
                </Button>

                <Button
                    variant="accent"
                    onClick={() => setFormOpen(true)}
                >
                    Form Modal
                </Button>
            </div>

            <Modal
                open={basicOpen}
                onClose={() => setBasicOpen(false)}
                title="Recipe Details"
                description="This is a reusable modal."
                footer={
                    <Button
                        onClick={() => setBasicOpen(false)}
                    >
                        Got It
                    </Button>
                }
            >
                <p>
                    You can place any React content here.
                </p>
            </Modal>

            <Modal
                open={confirmOpen}
                onClose={() => setConfirmOpen(false)}
                title="Remove Ingredient?"
                description="This action cannot be undone."
                size="sm"
                footer={
                    <>
                        <Button
                            variant="secondary"
                            onClick={() => setConfirmOpen(false)}
                        >
                            Cancel
                        </Button>

                        <Button
                            variant="accent"
                            onClick={() => setConfirmOpen(false)}
                        >
                            Remove
                        </Button>
                    </>
                }
            >
                <p>
                    Are you sure you want to remove this item?
                </p>
            </Modal>

            <Modal
                open={formOpen}
                onClose={() => setFormOpen(false)}
                title="Add Ingredient"
                size="md"
                footer={
                    <>
                        <Button
                            variant="secondary"
                            onClick={() => setFormOpen(false)}
                        >
                            Cancel
                        </Button>

                        <Button
                            type="submit"
                            form="modal-ingredient-form"
                        >
                            Save
                        </Button>
                    </>
                }
            >
                <form
                    id="modal-ingredient-form"
                    onSubmit={handleFormSubmit}
                >
                    <Input
                        label="Ingredient Name"
                        value={ingredient}
                        onChange={(event) =>
                            setIngredient(event.target.value)
                        }
                        placeholder="e.g. Tomato"
                        required
                    />
                </form>
            </Modal>
        </div>
    );
}

export default ModalExamples;
