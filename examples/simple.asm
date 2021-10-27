addi	sp,sp,-336
lui	a5,0x70
sd	s2,304(sp)
lui	s2,0x74
ld	a4,-1264(a5) # 6fb10 <__stack_chk_guard>
addi	a5,s2,-1488 # 73a30 <lock>
ld	a5,8(a5)
sd	s0,320(sp)
sd	s1,312(sp)
sd	ra,328(sp)
sd	s3,296(sp)
sd	a4,280(sp)
addi	s1,tp,-1808 # fffffffffffff8f0 <__BSS_END__+0xfffffffffff8b070>
addi	s0,s2,-1488
beq	a5,s1,1021c <abort+0x48>
li	a4,1
lr.w	a5,(s0)