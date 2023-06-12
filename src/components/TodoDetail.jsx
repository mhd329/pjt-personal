import React, { useState, useEffect, useCallback } from "react";
import { Button } from 'react-bootstrap';
import client from "../utils/client";
import cookie from "react-cookies";

function TodoDetail(props) {
    const handleClick = useCallback(() => {
        async function postTodo() {
            try {
                await client.post(`todo/detail/${}`, {
                    headers: {
                        Authorization: `Bearer ${cookie.load("access") ? cookie.load("access") : null}`,
                    },
                });
            } catch (AxiosResponse) {
                alert(AxiosResponse.response.data.message);
            };
        };
        postTodo();
    }, []);
    return (
        <div>
            <Button variant="primary" type="button" onClick={handleClick}>
                새로운 할 것
            </Button>
        </div>
    );
}

export default TodoDetail;