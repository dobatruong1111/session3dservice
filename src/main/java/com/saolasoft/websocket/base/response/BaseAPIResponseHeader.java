package com.saolasoft.websocket.base.response;

import java.io.Serializable;

public interface BaseAPIResponseHeader extends Serializable {

    int getCode();

    void setCode(int code);

    String getMessage();

    void setMessage(String message);
}
