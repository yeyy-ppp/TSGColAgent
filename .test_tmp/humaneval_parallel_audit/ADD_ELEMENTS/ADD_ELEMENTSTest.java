package humaneval.correct;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertDoesNotThrow;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

class ADD_ELEMENTSTest {
    @Test
    void aDD_ELEMENTS_add_elements_1_numericResult_1() {
        assertDoesNotThrow(() -> ADD_ELEMENTS.add_elements(java.util.Collections.emptyList(), 1));
    }

}
