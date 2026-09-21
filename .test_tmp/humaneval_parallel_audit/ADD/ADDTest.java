package humaneval.correct;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertDoesNotThrow;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

class ADDTest {
    @Test
    void aDD_add_1_arithmetic1_1() {
        assertEquals(3, ADD.add(1, 2));
    }

    @Test
    void aDD_add_1_arithmetic2_2() {
        assertEquals(1, ADD.add(-2, 3));
    }

    @Test
    void aDD_add_1_arithmetic3_3() {
        assertEquals(0, ADD.add(0, 0));
    }

}
