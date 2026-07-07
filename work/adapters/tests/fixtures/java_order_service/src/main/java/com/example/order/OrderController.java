package com.example.order;

import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/orders")
public class OrderController {
    @PostMapping
    public OrderResponse createOrder(@RequestBody CreateOrderRequest request) {
        return new OrderResponse();
    }
}
