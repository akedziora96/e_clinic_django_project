def prepare_table_rows(specializations_queryset, col):
    return [specializations_queryset[i:i+col] for i in range(0, len(specializations_queryset), col)]


if __name__ == "__main__":
    print(prepare_table_rows(list(range(0, 13)), 5))

