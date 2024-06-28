package com.saolasoft.websocket.session3d.model;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.Setter;
import java.util.List;

@Getter
@Setter
@AllArgsConstructor
public class Resource3d {
	
	private List<Integer> available;

	private List<Integer> used;
}
