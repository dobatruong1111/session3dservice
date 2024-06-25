package com.saolasoft.websocket.base.response;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.util.Date;

public class APIResponseHeader implements BaseAPIResponseHeader {

    private static final long serialVersionUID = 1L;

	private Date datetime = new Date();

    private int code;

    private String message;

    public APIResponseHeader() {
    }

    public APIResponseHeader(int code, String message) {
        this.code = code;
        this.message = message;
    }

    public APIResponseHeader(APIResponseStatus status, String message) {
        this.code = status.getValue();
        this.message = message;
    }

    public Date getDatetime() {
        return datetime;
    }

    public void setDatetime(Date datetime) {
        this.datetime = datetime;
    }

    public int getCode() {
        return code;
    }

    public void setCode(int code) {
        this.code = code;
    }

    public String getMessage() {
        return message;
    }

    public void setMessage(String message) {
        this.message = message;
    }



    @Override
    public String toString() {
        try {
            return new ObjectMapper().writeValueAsString(this);
        } catch (JsonProcessingException e) {
            return super.toString();
        }
    }
}
