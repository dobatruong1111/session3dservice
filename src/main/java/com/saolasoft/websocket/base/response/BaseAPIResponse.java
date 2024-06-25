package com.saolasoft.websocket.base.response;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.io.Serializable;

public class BaseAPIResponse<H extends BaseAPIResponseHeader, T> implements Serializable {

    private static final long serialVersionUID = 1L;
	private H header;
    private T body;

    public BaseAPIResponse() {
    }

    public BaseAPIResponse(H header, T body) {
        this.header = header;
        this.body = body;
    }

    public H getHeader() {
        return header;
    }

    public void setHeader(H header) {
        this.header = header;
    }

    public T getBody() {
        return body;
    }

    public void setBody(T body) {
        this.body = body;
    }

    @Override
    public String toString() {
        ObjectMapper mapper = new ObjectMapper();
        try {
            String json = mapper.writeValueAsString(this);
            return "[" + super.getClass().getSimpleName() + "] " + json;
        } catch (JsonProcessingException e) {
            return super.toString();
        }
    }
}
