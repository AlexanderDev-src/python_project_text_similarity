# Python Project - Text Similarity

### Algorithm

$TF(t, d) = \frac{f_{t,d}}{\sum_{t' \in d} f_{t',d}}$

$IDF(t, D) = \log\left(\frac{N}{df_t}\right)$

$TF\text{-}IDF(t, d, D) = TF(t, d) \times IDF(t, D)$

$\text{Cosine Similarity}(A, B) = \cos(\theta) = \frac{A \cdot B}{\|A\| \|B\|} = \frac{\sum_{i=1}^{n} A_i B_i}{\sqrt{\sum_{i=1}^{n} A_i^2} \sqrt{\sum_{i=1}^{n} B_i^2}}$

