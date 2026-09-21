package demo;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertDoesNotThrow;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

class CalculatorTest {
    @Test
    void calculator_add_1_arithmetic1_1() {
        assertEquals(3, new Calculator().add(1, 2));
    }

    @Test
    void calculator_add_1_arithmetic2_2() {
        assertEquals(1, new Calculator().add(-2, 3));
    }

    @Test
    void calculator_add_1_arithmetic3_3() {
        assertEquals(0, new Calculator().add(0, 0));
    }

}
